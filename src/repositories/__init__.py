"""Repository abstractions and implementations."""

from .base import Repository, ReadOnlyRepository, WriteableRepository
from .csv_repository import (
    CsvFileRepository,
    MultiPeriodCsvRepository,
    StoreCoordinatesRepository,
    SPUMappingRepository,
    SPUMetadataRepository
)
from .api_repository import FastFishApiRepository
from .tracking_repository import StoreTrackingRepository
from .period_discovery_repository import PeriodDiscoveryRepository
from .coordinate_extraction_repository import (
    CoordinateExtractionRepository,
    CoordinateData,
    ValidationResult
)
from .spu_aggregation_repository import SpuAggregationRepository
from .validation_repository import ValidationRepository
from .weather_api_repository import WeatherApiRepository
from .json_repository import JsonFileRepository, ProgressTrackingRepository
from .matrix_repository import MatrixRepository
from .temperature_repository import TemperatureRepository

__all__ = [
    "Repository",
    "ReadOnlyRepository",
    "WriteableRepository",
    "CsvFileRepository",
    "MultiPeriodCsvRepository",
    "StoreCoordinatesRepository",
    "SPUMappingRepository",
    "SPUMetadataRepository",
    "FastFishApiRepository",
    "StoreTrackingRepository",
    "PeriodDiscoveryRepository",
    "CoordinateExtractionRepository",
    "CoordinateData",
    "ValidationResult",
    "SpuAggregationRepository",
    "ValidationRepository",
    "WeatherApiRepository",
    "JsonFileRepository",
    "ProgressTrackingRepository",
    "MatrixRepository",
    "TemperatureRepository"
]
