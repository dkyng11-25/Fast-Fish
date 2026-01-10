"""
Pipeline steps following the 4-phase Step pattern.

⚠️ WARNING: Not all implementations in this module are recommended for use.

RECOMMENDED IMPLEMENTATIONS:
- ExtractCoordinatesStep (from extract_coordinates.py) - Test-compatible implementation
- ApiDownloadStep, MatrixPreparationStep, WeatherDataDownloadStep - Production ready

NOT RECOMMENDED:
- ExtractCoordinatesStepModular (from extract_coordinates_step.py) - Over-engineered modular implementation
- create_extract_coordinates_step - Factory for over-engineered implementation

For production: Use src/step2_extract_coordinates.py (enhanced legacy)
For testing: Use ExtractCoordinatesStep from extract_coordinates.py
"""

from .api_download_merge import ApiDownloadStep
from .extract_coordinates import ExtractCoordinatesStep
from .matrix_preparation_step import MatrixPreparationStep

__all__ = [
    "ApiDownloadStep",
    "ExtractCoordinatesStep",
    "MatrixPreparationStep",
    "WeatherDataDownloadStep"
]