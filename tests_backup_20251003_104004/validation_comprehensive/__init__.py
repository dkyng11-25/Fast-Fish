"""
Comprehensive Data Validation System

This package provides a complete, modular validation system for the Product Mix Clustering pipeline.
All validation schemas, utilities, and runners are organized in a single, comprehensive structure.

Author: Data Pipeline
Date: 2025-01-03
"""

# Core validation components
from .schemas import (
    # Time schemas
    TimeSeriesSchema, PeriodSchema, DateRangeSchema,
    
    # Weather schemas
    WeatherDataSchema, WeatherMetricsSchema, RadiationSchema,
    TemperatureSchema, PrecipitationSchema, WindSchema,
    HumiditySchema, PressureSchema, VisibilitySchema,
    StoreAltitudeSchema, WeatherExtremesSchema,
    
    # Step 5 schemas
    FeelsLikeTemperatureSchema, TemperatureBandsSchema, FeelsLikeCalculationSchema,
    
    # Step 2 schemas
    StoreCoordinatesSchema, SPUStoreMappingSchema, SPUMetadataSchema,
    
    # Step 2B schemas
    SeasonalStoreProfilesSchema, SeasonalCategoryPatternsSchema, SeasonalClusteringFeaturesSchema,
    
    # Step 3 schemas
    StoreMatrixSchema, SubcategoryMatrixSchema, SPUMatrixSchema, CategoryAggregatedMatrixSchema,
    
    # Step 6 schemas
    ClusteringResultsSchema, ClusterProfilesSchema, PerClusterMetricsSchema,
    
    # Product schemas
    StoreConfigSchema, CategorySalesSchema, SPUSalesSchema,
    StoreCodeSchema, ProductClassificationSchema,
    SalesSummarySchema, InventorySchema,
    
    # Common schemas
    GeographicSchema, SalesAmountSchema, QuantitySchema,
    PriceSchema, CountSchema, CategoricalSchema
)

from .validators import (
    validate_dataframe,
    validate_file,
    validate_multiple_files,
    get_validation_summary,
    log_validation_summary,
    safe_validate
)

from .runners import (
    validate_step1_period,
    validate_multiple_periods,
    validate_weather_files,
    validate_weather_by_period,
    run_comprehensive_validation
)

# Import complexity analyzer
from .complexity_analyzer import ValidationComplexityAnalyzer, ComplexityResult

__all__ = [
    # Time schemas
    'TimeSeriesSchema', 'PeriodSchema', 'DateRangeSchema',
    
    # Weather schemas
    'WeatherDataSchema', 'WeatherMetricsSchema', 'RadiationSchema',
    'TemperatureSchema', 'PrecipitationSchema', 'WindSchema',
    'HumiditySchema', 'PressureSchema', 'VisibilitySchema',
    'StoreAltitudeSchema', 'WeatherExtremesSchema',
    
        # Step 5 schemas
    'FeelsLikeTemperatureSchema', 'TemperatureBandsSchema', 'FeelsLikeCalculationSchema',

    # Step 2 schemas
    'StoreCoordinatesSchema', 'SPUStoreMappingSchema', 'SPUMetadataSchema',

    # Step 2B schemas
    'SeasonalStoreProfilesSchema', 'SeasonalCategoryPatternsSchema', 'SeasonalClusteringFeaturesSchema',

    # Step 3 schemas
    'StoreMatrixSchema', 'SubcategoryMatrixSchema', 'SPUMatrixSchema', 'CategoryAggregatedMatrixSchema',

    # Step 6 schemas
    'ClusteringResultsSchema', 'ClusterProfilesSchema', 'PerClusterMetricsSchema',

    # Product schemas
    'StoreConfigSchema', 'CategorySalesSchema', 'SPUSalesSchema',
    'StoreCodeSchema', 'ProductClassificationSchema',
    'SalesSummarySchema', 'InventorySchema',

    # Common schemas
    'GeographicSchema', 'SalesAmountSchema', 'QuantitySchema',
    'PriceSchema', 'CountSchema', 'CategoricalSchema',
    
    # Validators
    'validate_dataframe',
    'validate_file',
    'validate_multiple_files',
    'get_validation_summary',
    'log_validation_summary',
    'safe_validate',
    
    # Runners
    'validate_step1_period',
    'validate_multiple_periods',
    'validate_weather_files',
    'validate_weather_by_period',
    'validate_store_altitudes',
    'validate_step5_feels_like_temperature',
    'validate_feels_like_calculation_quality',
    'validate_step2_coordinates',
    'validate_step2b_seasonal_data',
    'validate_step3_matrices',
    'validate_step6_clustering',
    'run_step1_validation',
    'run_step2_validation',
    'run_step2b_validation',
    'run_step3_validation',
    'run_step4_validation',
    'run_step5_validation',
    'run_step6_validation',
    'run_comprehensive_validation',
    
    # Complexity analyzer
    'ValidationComplexityAnalyzer',
    'ComplexityResult'
]

__version__ = "1.0.0"
__author__ = "Data Pipeline"
