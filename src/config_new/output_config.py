"""
Output Configuration Module (Supports Over-engineered Modular Implementation - NOT RECOMMENDED)

⚠️ WARNING: This module supports overly complex modular implementations that are not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

Provides flexible output directory configuration for testing and comparison purposes.
Supports environment variable configuration and factory pattern for creating steps
with configurable output destinations.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

import os
from typing import Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from steps.extract_coordinates_step import ExtractCoordinatesStep
    from steps.matrix_preparation_step import MatrixPreparationStep


@dataclass
class OutputConfig:
    """
    Configuration class for output directories and file paths.

    Supports flexible output destinations for testing and comparison scenarios.
    """
    # Base output directory (can be overridden for testing)
    base_output_dir: str = "data"

    # Step-specific subdirectories
    step2_subdir: str = ""
    step3_subdir: str = ""

    # Environment variable overrides
    env_output_dir: Optional[str] = None
    env_step2_dir: Optional[str] = None
    env_step3_dir: Optional[str] = None

    # Testing mode flags
    use_temp_output: bool = False
    temp_suffix: str = "temp"

    def __post_init__(self):
        """Apply environment variable overrides after initialization."""
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Check for temp output mode
        if os.environ.get('PIPELINE_USE_TEMP_OUTPUT', 'false').lower() == 'true':
            self.use_temp_output = True

        # Override base output directory if specified
        env_base_dir = os.environ.get('PIPELINE_OUTPUT_DIR')
        if env_base_dir:
            self.base_output_dir = env_base_dir

        # Override step-specific directories if specified
        env_step2_dir = os.environ.get('PIPELINE_STEP2_OUTPUT_DIR')
        if env_step2_dir:
            self.step2_subdir = env_step2_dir

        env_step3_dir = os.environ.get('PIPELINE_STEP3_OUTPUT_DIR')
        if env_step3_dir:
            self.step3_subdir = env_step3_dir

        # Legacy environment variable support
        legacy_output_dir = os.environ.get('PIPELINE_TEMP_OUTPUT_DIR')
        if legacy_output_dir and self.use_temp_output:
            self.base_output_dir = legacy_output_dir

    @property
    def step2_output_dir(self) -> str:
        """Get the output directory for step 2."""
        if self.step2_subdir:
            return self.step2_subdir
        elif self.use_temp_output:
            return f"{self.base_output_dir}_{self.temp_suffix}"
        else:
            return self.base_output_dir

    @property
    def step3_output_dir(self) -> str:
        """Get the output directory for step 3."""
        if self.step3_subdir:
            return self.step3_subdir
        elif self.use_temp_output:
            return f"{self.base_output_dir}_{self.temp_suffix}"
        else:
            return self.base_output_dir

    def get_step2_file_path(self, filename: str) -> str:
        """Get full file path for step 2 output."""
        return os.path.join(self.step2_output_dir, filename)

    def get_step3_file_path(self, filename: str) -> str:
        """Get full file path for step 3 output."""
        return os.path.join(self.step3_output_dir, filename)


# Global configuration instance
_output_config = None


def get_output_config() -> OutputConfig:
    """
    Get the global output configuration instance.

    Returns:
        OutputConfig instance with current configuration
    """
    global _output_config
    if _output_config is None:
        _output_config = OutputConfig()
    return _output_config


def reset_output_config():
    """Reset the global output configuration (useful for testing)."""
    global _output_config
    _output_config = None


def configure_temp_output(temp_suffix: str = "temp", base_dir: str = "data"):
    """
    Configure output to use temporary directories for testing.

    Args:
        temp_suffix: Suffix to append to base directory name
        base_dir: Base output directory to use
    """
    os.environ['PIPELINE_USE_TEMP_OUTPUT'] = 'true'
    os.environ['PIPELINE_OUTPUT_DIR'] = base_dir
    reset_output_config()


def configure_step2_output(output_dir: str):
    """
    Configure specific output directory for step 2.

    Args:
        output_dir: Directory path for step 2 outputs
    """
    os.environ['PIPELINE_STEP2_OUTPUT_DIR'] = output_dir
    reset_output_config()


def configure_step3_output(output_dir: str):
    """
    Configure specific output directory for step 3.

    Args:
        output_dir: Directory path for step 3 outputs
    """
    os.environ['PIPELINE_STEP3_OUTPUT_DIR'] = output_dir
    reset_output_config()


def get_step2_coordinate_file() -> str:
    """Get the coordinate file path for step 2."""
    return get_output_config().get_step2_file_path("store_coordinates_extended.csv")


def get_step2_coordinate_period_file() -> str:
    """Get the period-specific coordinate file path for step 2."""
    config = get_output_config()
    period_label = os.environ.get('PIPELINE_TARGET_PERIOD', 'A')
    yyyymm = os.environ.get('PIPELINE_TARGET_YYYYMM', '202509')
    filename = f"store_coordinates_extended_{yyyymm}{period_label}.csv"
    return config.get_step2_file_path(filename)


def get_step2_spu_mapping_file() -> str:
    """Get the SPU mapping file path for step 2."""
    return get_output_config().get_step2_file_path("spu_store_mapping.csv")


def get_step2_spu_metadata_file() -> str:
    """Get the SPU metadata file path for step 2."""
    return get_output_config().get_step2_file_path("spu_metadata.csv")


def get_step3_subcategory_matrix_file() -> str:
    """Get the subcategory matrix file path for step 3."""
    return get_output_config().get_step3_file_path("store_subcategory_matrix.csv")


def get_step3_normalized_subcategory_matrix_file() -> str:
    """Get the normalized subcategory matrix file path for step 3."""
    return get_output_config().get_step3_file_path("normalized_subcategory_matrix.csv")


def get_step3_spu_matrix_file() -> str:
    """Get the SPU matrix file path for step 3."""
    return get_output_config().get_step3_file_path("store_spu_limited_matrix.csv")


def get_step3_normalized_spu_matrix_file() -> str:
    """Get the normalized SPU matrix file path for step 3."""
    return get_output_config().get_step3_file_path("normalized_spu_limited_matrix.csv")


def get_step3_category_matrix_file() -> str:
    """Get the category aggregated matrix file path for step 3."""
    return get_output_config().get_step3_file_path("store_category_agg_matrix.csv")


def get_step3_normalized_category_matrix_file() -> str:
    """Get the normalized category aggregated matrix file path for step 3."""
    return get_output_config().get_step3_file_path("normalized_category_agg_matrix.csv")


def get_step3_store_list_file() -> str:
    """Get the store list file path for step 3."""
    return get_output_config().get_step3_file_path("store_list.txt")


def get_step3_subcategory_list_file() -> str:
    """Get the subcategory list file path for step 3."""
    return get_output_config().get_step3_file_path("subcategory_list.txt")


def get_step3_category_list_file() -> str:
    """Get the category list file path for step 3."""
    return get_output_config().get_step3_file_path("category_list.txt")


# Convenience functions for creating steps with different output configurations

def create_step2_for_comparison(temp_suffix: str = "refactored") -> "ExtractCoordinatesStep":
    """
    Create over-engineered modular step 2 for comparison testing (NOT RECOMMENDED).

    ⚠️ WARNING: This creates an overly complex implementation using dependency injection.
    This approach is not recommended for production use due to unnecessary complexity.

    Args:
        temp_suffix: Suffix to append to output directory name

    Returns:
        Configured ExtractCoordinatesStep (over-engineered implementation)

    RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
    """
    from steps.extract_coordinates_step import create_extract_coordinates_step
    from core.logger import PipelineLogger

    logger = PipelineLogger()

    # Configure temp output
    temp_output_dir = f"data_{temp_suffix}"
    configure_temp_output(temp_suffix, "data")

    return create_extract_coordinates_step(temp_output_dir, logger, "Extract Coordinates and SPU Mappings", 2)


def create_step3_for_comparison(temp_suffix: str = "refactored") -> "MatrixPreparationStep":
    """
    Create step 3 configured for comparison testing with temp output.

    Args:
        temp_suffix: Suffix to append to output directory name

    Returns:
        Configured MatrixPreparationStep
    """
    from steps.matrix_preparation_step import MatrixPreparationStep
    from core.logger import PipelineLogger

    logger = PipelineLogger()

    # Configure temp output
    configure_temp_output(temp_suffix, "data")

    return MatrixPreparationStep(logger, "Matrix Preparation", 3)


def create_step2_with_custom_output(output_dir: str) -> "ExtractCoordinatesStep":
    """
    Create over-engineered modular step 2 with custom output directory (NOT RECOMMENDED).

    ⚠️ WARNING: This creates an overly complex implementation using dependency injection.
    This approach is not recommended for production use due to unnecessary complexity.

    Args:
        output_dir: Custom output directory path

    Returns:
        Configured ExtractCoordinatesStep (over-engineered implementation)

    RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
    """
    from steps.extract_coordinates_step import create_extract_coordinates_step
    from core.logger import PipelineLogger

    logger = PipelineLogger()

    # Configure custom output
    configure_step2_output(output_dir)

    return create_extract_coordinates_step(output_dir, logger, "Extract Coordinates and SPU Mappings", 2)


def create_step3_with_custom_output(output_dir: str) -> "MatrixPreparationStep":
    """
    Create step 3 with custom output directory.

    Args:
        output_dir: Custom output directory path

    Returns:
        Configured MatrixPreparationStep
    """
    from steps.matrix_preparation_step import MatrixPreparationStep
    from core.logger import PipelineLogger

    logger = PipelineLogger()

    # Configure custom output
    configure_step3_output(output_dir)

    return MatrixPreparationStep(logger, "Matrix Preparation", 3)
