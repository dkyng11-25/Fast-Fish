"""
Factory for creating FeelsLikeTemperatureStep with all dependencies.

This factory handles dependency injection for Step 5, creating all required
repositories and configuration objects.

Author: Data Pipeline Team
Date: 2025-10-10
"""

from typing import Optional
from pathlib import Path

from steps.feels_like_temperature_step import FeelsLikeTemperatureStep, FeelsLikeConfig
from repositories.weather_data_repository import WeatherDataRepository
from repositories.weather_file_repository import WeatherFileRepository
from repositories.weather_api_repository import WeatherApiRepository
from repositories.csv_repository import CsvFileRepository
from repositories.json_repository import ProgressTrackingRepository
from core.logger import PipelineLogger


def create_feels_like_temperature_step(
    target_yyyymm: Optional[str] = None,
    target_period: Optional[str] = None,
    coordinates_file: Optional[str] = None,
    logger: Optional[PipelineLogger] = None
) -> FeelsLikeTemperatureStep:
    """
    Create FeelsLikeTemperatureStep with all dependencies injected.
    
    This factory function creates and configures:
    - WeatherFileRepository for loading weather data
    - CsvFileRepository for altitude data
    - CsvFileRepository for temperature output (period-specific)
    - CsvFileRepository for bands output (period-specific)
    - FeelsLikeConfig with seasonal parameters
    - PipelineLogger if not provided
    
    Note: Follows Steps 1 & 2 pattern - separate repository per output file,
    period in filename, no timestamps or symlinks.
    
    Args:
        target_yyyymm: Target year-month (e.g., "202506")
        target_period: Target period ("A" or "B")
        coordinates_file: Path to coordinates CSV (default: 2stores)
        logger: Pipeline logger (creates new if None)
        
    Returns:
        Configured FeelsLikeTemperatureStep instance ready to execute
        
    Example:
        >>> step = create_feels_like_temperature_step("202506", "A")
        >>> context = StepContext()
        >>> result = step.execute(context)
    """
    # Create logger if not provided
    if logger is None:
        logger = PipelineLogger("FeelsLikeTemperature")
    
    # Default coordinates file
    if coordinates_file is None:
        coordinates_file = "data/store_coordinates_2stores.csv"
    
    # Create sub-repositories for WeatherDataRepository
    coordinates_repo = CsvFileRepository(
        file_path=str(Path(coordinates_file)),
        logger=logger
    )
    
    weather_api_repo = WeatherApiRepository(
        logger=logger
    )
    
    weather_file_repo = WeatherFileRepository(
        output_dir=str(Path("output")),
        logger=logger
    )
    
    altitude_repo = CsvFileRepository(
        file_path=str(Path("output/store_altitudes.csv")),
        logger=logger
    )
    
    progress_repo = ProgressTrackingRepository(
        file_path=str(Path("output/weather_download_progress.json")),
        logger=logger
    )
    
    # Create main WeatherDataRepository with all dependencies
    weather_data_repo = WeatherDataRepository(
        coordinates_repo=coordinates_repo,
        weather_api_repo=weather_api_repo,
        weather_file_repo=weather_file_repo,
        altitude_repo=altitude_repo,
        progress_repo=progress_repo,
        logger=logger
    )
    
    # Create output repositories (one per output file, following Steps 1 & 2 pattern)
    # Include period in filename for explicit period tracking
    period_label = f"{target_yyyymm}{target_period}" if target_yyyymm and target_period else ""
    
    temperature_output_repo = CsvFileRepository(
        file_path=str(Path(f"output/stores_with_feels_like_temperature_{period_label}.csv")),
        logger=logger
    )
    
    bands_output_repo = CsvFileRepository(
        file_path=str(Path(f"output/temperature_bands_{period_label}.csv")),
        logger=logger
    )
    
    # Create configuration with seasonal parameters
    config = FeelsLikeConfig(
        seasonal_focus_months=[9, 11],  # September and November
        lookback_years=2,
        seasonal_band_column="temperature_band_q3q4_seasonal",
        seasonal_feels_like_column="feels_like_temperature_q3q4_seasonal",
        temperature_band_size=5  # 5-degree Celsius bands
    )
    
    # Create and return step instance
    return FeelsLikeTemperatureStep(
        weather_data_repo=weather_data_repo,
        altitude_repo=altitude_repo,
        temperature_output_repo=temperature_output_repo,
        bands_output_repo=bands_output_repo,
        config=config,
        logger=logger,
        step_name="Feels-Like Temperature",
        step_number=5,
        target_yyyymm=target_yyyymm,
        target_period=target_period
    )
