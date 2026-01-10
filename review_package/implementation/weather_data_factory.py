#!/usr/bin/env python3
"""
Factory function for Step 4: Weather Data Download

This is the composition root for Step 4 - all dependency injection happens here.
This function creates and wires all dependencies for the WeatherDataDownloadStep.
"""

from pathlib import Path
from typing import Optional

from steps.weather_data_download_step import WeatherDataDownloadStep, StepConfig
from repositories import (
    CsvFileRepository,
    JsonFileRepository,
    WeatherApiRepository,
    ProgressTrackingRepository
)
from core.logger import PipelineLogger


def create_weather_data_download_step(
    coordinates_path: str,
    weather_output_dir: str,
    altitude_output_path: str,
    progress_file_path: str,
    target_yyyymm: Optional[str] = None,
    target_period: Optional[str] = None,
    months_back: int = 3,
    stores_per_vpn_batch: int = 50,
    min_delay: float = 0.5,
    max_delay: float = 1.5,
    rate_limit_backoff_min: float = 5.0,
    rate_limit_backoff_max: float = 20.0,
    max_retries: int = 3,
    vpn_switch_threshold: int = 5,
    timezone: str = 'Asia/Shanghai',
    enable_vpn_switching: bool = True,
    logger: Optional[PipelineLogger] = None
) -> WeatherDataDownloadStep:
    """
    Factory function to create Step 4 with all dependencies.
    
    This is the composition root - all dependency injection happens here.
    
    Args:
        coordinates_path: Path to store coordinates CSV file
        weather_output_dir: Directory for weather data output
        altitude_output_path: Path for altitude data CSV
        progress_file_path: Path for progress tracking JSON
        target_yyyymm: Target year-month (e.g., "202506")
        target_period: Target period ("A" or "B")
        months_back: Number of months to look back for year-over-year
        stores_per_vpn_batch: Stores to process before VPN switch prompt
        min_delay: Minimum delay between API requests (seconds)
        max_delay: Maximum delay between API requests (seconds)
        rate_limit_backoff_min: Minimum backoff for rate limiting (seconds)
        rate_limit_backoff_max: Maximum backoff for rate limiting (seconds)
        max_retries: Maximum retry attempts for failed requests
        vpn_switch_threshold: Consecutive failures before VPN switch prompt
        timezone: Timezone for weather data (default: Asia/Shanghai)
        enable_vpn_switching: Enable VPN switching support
        logger: Optional logger instance (creates new one if not provided)
    
    Returns:
        WeatherDataDownloadStep: Fully configured step instance
    
    Example:
        >>> # Create step for June 2025, period A
        >>> step = create_weather_data_download_step(
        ...     coordinates_path="data/store_coordinates.csv",
        ...     weather_output_dir="data/weather",
        ...     altitude_output_path="data/altitude.csv",
        ...     progress_file_path="data/progress.json",
        ...     target_yyyymm="202506",
        ...     target_period="A"
        ... )
        >>> 
        >>> # Execute the step
        >>> from core.context import StepContext
        >>> context = StepContext()
        >>> final_context = step.execute(context)
    """
    # Create logger if not provided
    if logger is None:
        logger = PipelineLogger("Step4_WeatherDataDownload")
    
    # Create repositories
    coordinates_repo = CsvFileRepository(
        file_path=coordinates_path,
        logger=logger
    )
    
    weather_output_repo = CsvFileRepository(
        file_path=weather_output_dir,  # Directory for weather files
        logger=logger
    )
    
    altitude_repo = CsvFileRepository(
        file_path=altitude_output_path,
        logger=logger
    )
    
    # Create weather API repository
    weather_api_repo = WeatherApiRepository(
        logger=logger
    )
    
    # Create progress tracking repository
    progress_repo = ProgressTrackingRepository(
        file_path=progress_file_path,
        logger=logger
    )
    
    # Create configuration
    config = StepConfig(
        months_back=months_back,
        stores_per_vpn_batch=stores_per_vpn_batch,
        min_delay=min_delay,
        max_delay=max_delay,
        rate_limit_backoff_min=rate_limit_backoff_min,
        rate_limit_backoff_max=rate_limit_backoff_max,
        max_retries=max_retries,
        vpn_switch_threshold=vpn_switch_threshold,
        timezone=timezone,
        enable_vpn_switching=enable_vpn_switching
    )
    
    # Create and return step with all dependencies injected
    return WeatherDataDownloadStep(
        coordinates_repo=coordinates_repo,
        weather_api_repo=weather_api_repo,
        weather_output_repo=weather_output_repo,
        altitude_repo=altitude_repo,
        progress_repo=progress_repo,
        config=config,
        logger=logger,
        step_name="Weather Data Download",
        step_number=4,
        target_yyyymm=target_yyyymm,
        target_period=target_period
    )


# Example usage (for documentation and testing)
if __name__ == "__main__":
    import os
    from core.context import StepContext
    from core.exceptions import DataValidationError
    
    # Get configuration from environment variables
    target_yyyymm = os.environ.get('PIPELINE_TARGET_YYYYMM', '202506')
    target_period = os.environ.get('PIPELINE_TARGET_PERIOD', 'A')
    
    print(f"Creating Step 4 for period {target_yyyymm}{target_period}")
    
    # Create step with dependencies
    step = create_weather_data_download_step(
        coordinates_path="data/store_coordinates.csv",
        weather_output_dir="data/weather",
        altitude_output_path="data/altitude.csv",
        progress_file_path="data/weather_progress.json",
        target_yyyymm=target_yyyymm,
        target_period=target_period,
        months_back=3
    )
    
    # Create initial context
    context = StepContext()
    
    # Execute step
    try:
        print("Executing Step 4...")
        final_context = step.execute(context)
        print("✅ Step 4 completed successfully")
        
        # Show summary
        periods = final_context.get_state('periods', [])
        print(f"Generated {len(periods)} periods for download")
        
    except DataValidationError as e:
        print(f"❌ Step 4 validation failed: {e}")
        raise
    except Exception as e:
        print(f"❌ Step 4 execution failed: {e}")
        raise
